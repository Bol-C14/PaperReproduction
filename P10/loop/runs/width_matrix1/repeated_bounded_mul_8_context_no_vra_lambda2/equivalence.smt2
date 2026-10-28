; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x179 (bvmul ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))))))))
(let ((?x121 ((_ extract 7 0) ?x179)))
(let (($x91 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x67 (ite $x91 (bvadd ?x121 ?x121) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))
(let ((?x5 ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b))))))
(and (distinct (ite $x91 (bvadd ?x5 ?x5) c) ?x67) true)))))))
(check-sat)
