; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x164 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x161 ((_ extract 15 0) (bvmul ((_ extract 15 0) ((_ extract 15 0) a)) ((_ zero_extend 13) ((_ extract 2 0) ((_ extract 2 0) b)))))))
(let ((?x37 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) (bvadd ?x161 ?x161)))))))))
(let (($x19 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x471 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x19 (bvadd ?x471 ?x471) c) (ite $x19 ?x37 ?x164)) true)))))))
(check-sat)
