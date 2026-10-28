; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x32 (bvmul ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 15 0) ((_ extract 15 0) a)))) ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b))))))))
(let ((?x121 ((_ zero_extend 1) ((_ extract 4 0) ((_ zero_extend 11) ?x32)))))
(let (($x565 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x24 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x565 (bvadd ?x24 ?x24) c) (ite $x565 ((_ zero_extend 10) (bvadd ?x121 ?x121)) ((_ extract 15 0) ((_ extract 15 0) c)))) true))))))
(check-sat)
